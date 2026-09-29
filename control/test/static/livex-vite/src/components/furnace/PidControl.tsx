import { Row, Col, Form, FloatingLabel } from 'react-bootstrap';
import { TitleCard, EndpointInput, EndpointButton } from '@dssg/odin-react';
import type { AdapterEndpoint } from '@dssg/odin-react';
import type { FurnaceEndpointTypes } from '../../EndpointTypes';
import { checkNull  } from '../../utils';

import { floatingInputStyle } from '../../utils';

interface PidControlProps {
    furnaceEndPoint: AdapterEndpoint<FurnaceEndpointTypes>;
    connectedDisable: boolean;
    title: string;
    pid: "pid_upper" | "pid_lower";
}

type PidBranch = FurnaceEndpointTypes['pid_upper' | 'pid_lower'];

function PidControl(props: PidControlProps) {
    const { furnaceEndPoint, connectedDisable, title, pid } = props;
    const pidData = furnaceEndPoint.data?.[pid] as PidBranch | undefined;

    return (
      <TitleCard
        title={
          <Row>
            <Col xs={3} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>{title}</Col>
            <Col xs={3}>
              <EndpointButton
                endpoint={furnaceEndPoint}
                fullpath={pid+"/enable"}
                variant={pidData?.enable ? 'danger' : 'primary'}
                value={pidData?.enable ? false : true}
                >
                  {pidData?.enable ? "Disable" : "Enable"}
              </EndpointButton>
            </Col>
          </Row>
        }>
        <Row>
          <Col>
            <Row>
              <Col xs={6}>
                <FloatingLabel
                  label="Proportional">
                    <EndpointInput
                      endpoint={furnaceEndPoint}
                      fullpath={pid+"/proportional"}
                      disabled={connectedDisable}
                    />
                </FloatingLabel>
                  <FloatingLabel
                  label="Integral">
                    <EndpointInput
                      endpoint={furnaceEndPoint}
                      fullpath={pid+"/integral"}
                      disabled={connectedDisable}
                    />
                </FloatingLabel>
                <FloatingLabel
                  label="Derivative">
                    <EndpointInput
                      endpoint={furnaceEndPoint}
                      fullpath={pid+"/derivative"}
                      disabled={connectedDisable}
                    />
                </FloatingLabel>
              </Col>
              <Col xs={6}>
                <Row>
                  <Col> {/* This Col avoids minor FloatingLabel positioning bug */}
                    <FloatingLabel
                      label="Enter set pt.">
                        <EndpointInput
                          endpoint={furnaceEndPoint}
                          fullpath={pid+"/setpoint"}
                          disabled={connectedDisable}
                        />
                    </FloatingLabel>
                  </Col>
                </Row>
                <Row>
                  <Col>
                    <FloatingLabel label="Current set pt.">
                      <Form.Control
                        plaintext
                        readOnly
                        style={{
                          width: "100%",
                          border: '1px solid lightblue',
                          backgroundColor: '#e0f7ff',
                          borderRadius: '0.375rem'
                        }}
                        value={checkNull(pidData?.setpoint)}
                      />
                    </FloatingLabel>
                  </Col>
                </Row>
                <Row>
                  <Col xs={8} sm={6}>
                    <FloatingLabel
                      label="Temperature">
                        <Form.Control
                          plaintext
                          readOnly
                          style={{
                              width: "100%",
                              border: '1px solid lightblue',
                              backgroundColor: '#e0f7ff',
                              borderRadius: '0.375rem'
                          }}

                          value={checkNull(pidData?.temperature)}
                        />
                    </FloatingLabel>
                  </Col>
                  <Col xs={8} sm={6}>
                    <FloatingLabel
                      label="Set/target diff.">
                        <Form.Control
                          plaintext
                          readOnly
                          style={{
                              width: "100%",
                              border: '1px solid lightblue',
                              backgroundColor: '#e0f7ff',
                              borderRadius: '0.375rem'
                          }}
                          value={
                            checkNull(Math.abs(
                              (pidData?.setpoint ?? 0) -
                              (pidData?.temperature ?? 0))
                            )
                          }
                        />
                    </FloatingLabel>
                  </Col>
                </Row>
              </Col>
            </Row>
          </Col>
        </Row>
      </TitleCard>
    )
}

export default PidControl;