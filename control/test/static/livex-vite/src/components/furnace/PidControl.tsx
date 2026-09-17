import { Row, Col, Form, FloatingLabel } from 'react-bootstrap';
import { TitleCard, WithEndpoint, EndpointButton } from 'odin-react';
import type { AdapterEndpoint } from 'odin-react';
import type { FurnaceEndpointTypes } from '../../EndpointTypes';
import { checkNull  } from '../../utils';

import { floatingInputStyle } from '../../utils';

const EndPointFormControl = WithEndpoint(Form.Control);

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
                    <EndPointFormControl
                      endpoint={furnaceEndPoint}
                      type="number"
                      fullpath={pid+"/proportional"}
                      disabled={connectedDisable}
                      style={floatingInputStyle}
                    />
                </FloatingLabel>
                  <FloatingLabel
                  label="Integral">
                    <EndPointFormControl
                      endpoint={furnaceEndPoint}
                      type="number"
                      fullpath={pid+"/integral"}
                      disabled={connectedDisable}
                      style={floatingInputStyle}
                    />
                </FloatingLabel>
                <FloatingLabel
                  label="Derivative">
                    <EndPointFormControl
                      endpoint={furnaceEndPoint}
                      type="number"
                      fullpath={pid+"/derivative"}
                      disabled={connectedDisable}
                      style={floatingInputStyle}
                    />
                </FloatingLabel>
              </Col>
              <Col xs={6}>
                <Row>
                  <Col> {/* This Col avoids minor FloatingLabel positioning bug */}
                    <FloatingLabel
                      label="Enter set pt.">
                        <EndPointFormControl
                          endpoint={furnaceEndPoint}
                          type="number"
                          fullpath={pid+"/setpoint"}
                          disabled={connectedDisable}
                          style={floatingInputStyle}
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