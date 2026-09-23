import type { FurnaceEndpointTypes } from '../../EndpointTypes';

import { Col, Row, FloatingLabel } from 'react-bootstrap';
import { type AdapterEndpoint, TitleCard, EndpointInput } from '@dssg/odin-react';
import { floatingInputStyle } from '../../utils';

interface FurnaceMetaProps {
  furnaceEndPoint: AdapterEndpoint<FurnaceEndpointTypes>;
  connectedDisable: boolean;
}

function FurnaceMeta(props: FurnaceMetaProps) {
    const { furnaceEndPoint, connectedDisable } = props;

    return (
      <TitleCard title={
        <Row>
          <Col xs={6} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Furnace Settings</Col>
        </Row>
      }>
        <Col>
          <Row>
            <Col xs={6}>
              <FloatingLabel label="Max Setpoint">
                <EndpointInput
                  endpoint={furnaceEndPoint}
                  fullpath={"max_setpoint"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
            <Col xs={6}>
              <FloatingLabel label="Max Setpoint Increase">
                <EndpointInput
                  endpoint={furnaceEndPoint}
                  fullpath={"max_setpoint_increase"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
          </Row>
          <Row className="mt-3">
            <Col xs={6}>
              <FloatingLabel label="Upper Output Power Scalar">
                <EndpointInput
                  endpoint={furnaceEndPoint}
                  fullpath={"pid_upper/output_scalar"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
            <Col xs={6}>
              <FloatingLabel label="Lower Output Power Scalar">
                <EndpointInput
                  endpoint={furnaceEndPoint}
                  fullpath={"pid_lower/output_scalar"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
          </Row>
        </Col>
          
      </TitleCard>
    )
}

export default FurnaceMeta;